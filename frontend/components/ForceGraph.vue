<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
  GRAPH_TYPE_COLORS,
  GRAPH_TYPE_LABELS,
  GRAPH_RELATION_LABELS,
  GRAPH_RELATION_COLORS,
} from "~/utils/graph";

export interface GraphNode {
  id: string;
  label?: string;
  tipo?: string;
  type?: string;
  ref?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  tipo?: string;
  type?: string;
  peso?: number;
}

interface SimPoint {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const props = withDefaults(
  defineProps<{
    nodes: GraphNode[];
    links: GraphLink[];
    showControls?: boolean;
    showLegend?: boolean;
    initialHeight?: number;
  }>(),
  {
    showControls: true,
    showLegend: true,
    initialHeight: 520,
  }
);

const emit = defineEmits<{
  (e: "node-click", node: GraphNode): void;
}>();

const W = 960;
const H = 580;

const positions = ref<Map<string, SimPoint>>(new Map());
const hovered = ref<GraphNode | null>(null);
const mousePos = ref<{ x: number; y: number } | null>(null);
const svgEl = ref<SVGSVGElement | null>(null);

function getNodeType(node: GraphNode): string {
  return (node.tipo || node.type || "entity").toLowerCase();
}

function colorFor(type?: string): string {
  if (!type) return "#94a3b8";
  const key = type.toLowerCase();
  return GRAPH_TYPE_COLORS[key] || "#7c3aed";
}

function radiusFor(type?: string): number {
  const t = (type || "").toLowerCase();
  if (t === "case") return 20;
  if (t === "news") return 14;
  if (t === "indicator") return 13;
  if (t === "event") return 13;
  return 10;
}

// ---------------------------------------------------------------------------
// Simulación física continua (fuerza dirigida)
// ---------------------------------------------------------------------------
const REPULSION = 5200;
const SPRING_LEN = 115;
const SPRING_K = 0.032;
const GRAVITY = 0.012;
const MAX_SPEED = 12;

let alpha = 0;
let rafId = 0;
const pinned = new Set<string>();

function seedPositions() {
  const pos = positions.value;
  const seen = new Set<string>();
  props.nodes.forEach((n, i) => {
    seen.add(n.id);
    if (!pos.has(n.id)) {
      const angle = (i / Math.max(props.nodes.length, 1)) * Math.PI * 2;
      const radius = getNodeType(n) === "case" ? 20 : 170 + (Math.random() - 0.5) * 50;
      pos.set(n.id, {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      });
    }
  });
  for (const id of [...pos.keys()]) {
    if (!seen.has(id)) pos.delete(id);
  }
}

function step() {
  const pos = positions.value;
  const ids = [...pos.keys()];
  const pairs = props.links.filter((l) => pos.has(l.source) && pos.has(l.target));

  // 1. Repulsión electrostática entre todos los pares
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const a = pos.get(ids[i])!;
      const b = pos.get(ids[j])!;
      let dx = a.x - b.x;
      let dy = a.y - b.y;
      let distSq = dx * dx + dy * dy;
      if (distSq < 1) {
        dx = Math.random() - 0.5;
        dy = Math.random() - 0.5;
        distSq = 1;
      }
      const dist = Math.sqrt(distSq);
      const force = Math.min(REPULSION / distSq, 30) * alpha;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      if (!pinned.has(ids[i])) {
        a.vx += fx;
        a.vy += fy;
      }
      if (!pinned.has(ids[j])) {
        b.vx -= fx;
        b.vy -= fy;
      }
    }
  }

  // 2. Resortes en las aristas conectadas
  for (const l of pairs) {
    const a = pos.get(l.source)!;
    const b = pos.get(l.target)!;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
    const force = (dist - SPRING_LEN) * SPRING_K * alpha;
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    if (!pinned.has(l.source)) {
      a.vx += fx;
      a.vy += fy;
    }
    if (!pinned.has(l.target)) {
      b.vx -= fx;
      b.vy -= fy;
    }
  }

  // 3. Gravedad hacia el centro y amortiguación
  for (const [id, p] of pos) {
    if (pinned.has(id)) continue;
    p.vx -= p.x * GRAVITY * alpha;
    p.vy -= p.y * GRAVITY * alpha;
    const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
    if (speed > MAX_SPEED) {
      p.vx = (p.vx / speed) * MAX_SPEED;
      p.vy = (p.vy / speed) * MAX_SPEED;
    }
    p.x += p.vx;
    p.y += p.vy;
    p.vx *= 0.82;
    p.vy *= 0.82;
  }
}

function loop() {
  rafId = 0;
  if (alpha < 0.008) return;
  step();
  alpha *= 0.985;
  rafId = requestAnimationFrame(loop);
}

function reheat(strength = 1) {
  alpha = Math.max(alpha, strength);
  if (!rafId) rafId = requestAnimationFrame(loop);
}

function centerMass() {
  const pos = positions.value;
  if (!pos.size) return;
  let cx = 0;
  let cy = 0;
  for (const p of pos.values()) {
    cx += p.x;
    cy += p.y;
  }
  cx /= pos.size;
  cy /= pos.size;
  for (const p of pos.values()) {
    p.x -= cx;
    p.y -= cy;
  }
}

function rebuild() {
  seedPositions();
  centerMass();
  reheat(1);
}

watch(() => [props.nodes, props.links] as const, rebuild, { deep: true, immediate: true });

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId);
});

// ---------------------------------------------------------------------------
// Cámara: Zoom, Paneo y ViewBox
// ---------------------------------------------------------------------------
const view = ref({ x: 0, y: 0, k: 1 });
const MIN_K = 0.35;
const MAX_K = 4;

const viewBox = computed(() => {
  const { x, y, k } = view.value;
  return `${x - (W / 2) * k} ${y - (H / 2) * k} ${W * k} ${H * k}`;
});

let panState: { startX: number; startY: number; viewX: number; viewY: number } | null = null;
let dragId: string | null = null;
let hasDraggedNode = false;

function toSvg(evt: { clientX: number; clientY: number }): { x: number; y: number } {
  const svg = svgEl.value;
  if (!svg) return { x: 0, y: 0 };
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  return new DOMPoint(evt.clientX, evt.clientY).matrixTransform(ctm.inverse());
}

function onSvgDown(evt: PointerEvent) {
  if (dragId) return;
  const p = toSvg(evt);
  panState = { startX: p.x, startY: p.y, viewX: view.value.x, viewY: view.value.y };
  svgEl.value?.setPointerCapture(evt.pointerId);
}

function onWheel(evt: WheelEvent) {
  evt.preventDefault();
  const p = toSvg(evt);
  const k = Math.min(MAX_K, Math.max(MIN_K, view.value.k * Math.exp(-evt.deltaY * 0.0012)));
  const ratio = k / view.value.k;
  view.value.x = p.x - (p.x - view.value.x) * ratio;
  view.value.y = p.y - (p.y - view.value.y) * ratio;
  view.value.k = k;
}

function resetView() {
  view.value = { x: 0, y: 0, k: 1 };
  reheat(0.8);
}

function zoomIn() {
  view.value.k = Math.min(MAX_K, view.value.k * 1.3);
}

function zoomOut() {
  view.value.k = Math.max(MIN_K, view.value.k * 0.7);
}

defineExpose({ resetView, zoomIn, zoomOut });

function onNodeDown(node: GraphNode, evt: PointerEvent) {
  evt.preventDefault();
  evt.stopPropagation();
  dragId = node.id;
  hasDraggedNode = false;
  pinned.add(node.id);
  hovered.value = node;
  svgEl.value?.setPointerCapture(evt.pointerId);
}

function onSvgMove(evt: PointerEvent) {
  const p = toSvg(evt);
  mousePos.value = p;
  if (dragId) {
    hasDraggedNode = true;
    const pt = positions.value.get(dragId);
    if (pt) {
      pt.x = p.x;
      pt.y = p.y;
      pt.vx = 0;
      pt.vy = 0;
    }
  } else if (panState) {
    view.value.x = panState.viewX - (p.x - panState.startX) / view.value.k;
    view.value.y = panState.viewY - (p.y - panState.startY) / view.value.k;
  }
}

function onSvgUp(evt: PointerEvent) {
  if (dragId) {
    const releasedId = dragId;
    pinned.delete(dragId);
    dragId = null;
    svgEl.value?.releasePointerCapture(evt.pointerId);
    reheat(0.5);

    // Si no hubo arrastre apreciable, considerarlo un clic
    if (!hasDraggedNode) {
      const clickedNode = props.nodes.find((n) => n.id === releasedId);
      if (clickedNode) {
        emit("node-click", clickedNode);
      }
    }
  }
  panState = null;
}

function onSvgLeave() {
  if (!dragId) {
    mousePos.value = null;
    hovered.value = null;
  }
}

// ---------------------------------------------------------------------------
// Resaltado de vecindarios y opacidad
// ---------------------------------------------------------------------------
const highlightedIds = computed<Set<string> | null>(() => {
  if (!hovered.value) return null;
  const set = new Set([hovered.value.id]);
  for (const l of props.links) {
    if (l.source === hovered.value.id) set.add(l.target);
    if (l.target === hovered.value.id) set.add(l.source);
  }
  return set;
});

function isLinkHighlighted(link: GraphLink): boolean {
  return !!hovered.value && (link.source === hovered.value.id || link.target === hovered.value.id);
}

function nodeOpacity(node: GraphNode): number {
  const hi = highlightedIds.value;
  if (!hi) return 1;
  return hi.has(node.id) ? 1 : 0.18;
}

function linkOpacity(link: GraphLink): number {
  if (!hovered.value) return 0.65;
  return isLinkHighlighted(link) ? 1 : 0.08;
}

function linkStroke(link: GraphLink): string {
  if (isLinkHighlighted(link)) return "#0284c7";
  const t = (link.tipo || link.type || "").toLowerCase();
  return GRAPH_RELATION_COLORS[t] || "#94a3b8";
}

const tooltipFlip = computed(() => {
  const m = mousePos.value;
  if (!m) return false;
  return m.x - view.value.x > (W * view.value.k) / 4;
});

const tooltipX = computed(() => {
  const m = mousePos.value;
  if (!m) return 0;
  return tooltipFlip.value ? m.x - 20 : m.x + 20;
});

const tooltipAnchor = computed(() => (tooltipFlip.value ? "end" : "start"));

function point(id: string): SimPoint {
  return positions.value.get(id) ?? { x: 0, y: 0, vx: 0, vy: 0 };
}

const activeLegendTypes = computed(() => {
  const set = new Set<string>();
  for (const n of props.nodes) {
    set.add(getNodeType(n));
  }
  return [...set];
});
</script>

<template>
  <div class="relative w-full rounded-lg border border-hairline bg-surface overflow-hidden shadow-ev-1 select-none">
    <!-- Floating Toolbar -->
    <div
      v-if="showControls"
      class="absolute top-3 right-3 z-10 flex items-center gap-1.5 p-1 rounded-md bg-surface/90 backdrop-blur-md border border-hairline shadow-ev-1 text-caption"
    >
      <button
        type="button"
        class="h-7 w-7 rounded-sm flex items-center justify-center hover:bg-surface-sunken font-bold text-ink-muted hover:text-ink transition-colors cursor-pointer"
        title="Acercar (Zoom In)"
        @click="zoomIn"
      >
        +
      </button>
      <button
        type="button"
        class="h-7 w-7 rounded-sm flex items-center justify-center hover:bg-surface-sunken font-bold text-ink-muted hover:text-ink transition-colors cursor-pointer"
        title="Alejar (Zoom Out)"
        @click="zoomOut"
      >
        −
      </button>
      <div class="h-4 w-px bg-hairline"></div>
      <button
        type="button"
        class="h-7 px-2.5 rounded-sm flex items-center gap-1.5 hover:bg-surface-sunken text-[11px] font-medium text-ink-muted hover:text-ink transition-colors cursor-pointer"
        title="Centrar vista del grafo"
        @click="resetView"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
        <span>Centrar</span>
      </button>
    </div>

    <!-- Stats pill top left -->
    <div class="absolute top-3 left-3 z-10 flex items-center gap-2 p-1 px-2.5 rounded-sm bg-surface/90 backdrop-blur-md border border-hairline text-[11px] font-mono tabular-nums text-ink-muted shadow-ev-1">
      <span>{{ nodes.length }} nodos</span>
      <span>·</span>
      <span>{{ links.length }} enlaces</span>
    </div>

    <!-- Interactive SVG Graph Canvas -->
    <svg
      ref="svgEl"
      :viewBox="viewBox"
      class="w-full cursor-grab touch-none select-none active:cursor-grabbing transition-colors"
      :style="{ height: `${initialHeight}px` }"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Grafo interactivo de dependencias GraphRAG"
      @pointerdown="onSvgDown"
      @pointermove="onSvgMove"
      @pointerup="onSvgUp"
      @pointercancel="onSvgUp"
      @pointerleave="onSvgLeave"
      @wheel="onWheel"
    >
      <defs>
        <!-- Gradients and markers -->
        <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.25" />
        </filter>
      </defs>

      <!-- Graph Links / Edges -->
      <g>
        <line
          v-for="(link, i) in links"
          :key="`l-${i}`"
          :x1="point(link.source).x"
          :y1="point(link.source).y"
          :x2="point(link.target).x"
          :y2="point(link.target).y"
          :stroke="linkStroke(link)"
          :stroke-width="isLinkHighlighted(link) ? 2.5 : 1.3"
          :opacity="linkOpacity(link)"
          class="transition-opacity duration-150"
        />
      </g>

      <!-- Graph Nodes -->
      <g
        v-for="node in nodes"
        :key="node.id"
        :opacity="nodeOpacity(node)"
        class="transition-opacity duration-150"
      >
        <!-- Highlight halo if hovered -->
        <circle
          v-if="hovered && node.id === hovered.id"
          :cx="point(node.id).x"
          :cy="point(node.id).y"
          :r="radiusFor(getNodeType(node)) + 8"
          :fill="colorFor(getNodeType(node))"
          opacity="0.25"
        />

        <!-- Node Circle -->
        <circle
          :cx="point(node.id).x"
          :cy="point(node.id).y"
          :r="radiusFor(getNodeType(node))"
          :fill="colorFor(getNodeType(node))"
          fill-opacity="0.9"
          stroke="rgba(255, 255, 255, 0.9)"
          stroke-width="1.5"
          filter="url(#node-shadow)"
          class="cursor-pointer transition hover:fill-opacity-100"
          @pointerdown="onNodeDown(node, $event)"
          @pointerenter="hovered = node"
          @pointerleave="hovered = dragId === node.id ? hovered : null"
        />

        <!-- Node Label -->
        <text
          v-if="nodes.length <= 60 || (highlightedIds && highlightedIds.has(node.id)) || getNodeType(node) === 'case'"
          :x="point(node.id).x"
          :y="point(node.id).y + radiusFor(getNodeType(node)) + 13"
          text-anchor="middle"
          class="fill-ink text-[10px] font-sans font-medium tracking-tight pointer-events-none drop-shadow-xs"
        >
          {{ (node.label || node.id).slice(0, 24) }}
        </text>
      </g>

      <!-- Cursor Tooltip -->
      <g v-if="hovered && mousePos" pointer-events="none">
        <rect
          :x="tooltipFlip ? tooltipX - 220 : tooltipX"
          :y="mousePos.y - 42"
          rx="6"
          width="220"
          height="54"
          class="fill-surface stroke-hairline"
          filter="url(#node-shadow)"
        />
        <text
          :x="tooltipFlip ? tooltipX - 10 : tooltipX + 10"
          :y="mousePos.y - 23"
          :text-anchor="tooltipAnchor"
          class="fill-ink text-xs font-semibold"
        >
          {{ (hovered.label || hovered.id).slice(0, 28) }}
        </text>
        <text
          :x="tooltipFlip ? tooltipX - 10 : tooltipX + 10"
          :y="mousePos.y - 7"
          :text-anchor="tooltipAnchor"
          class="fill-ink-muted text-[10px]"
        >
          {{ GRAPH_TYPE_LABELS[getNodeType(hovered)] || getNodeType(hovered) }} · Clic para abrir contenido
        </text>
      </g>
    </svg>

    <!-- Legend bar at bottom -->
    <div
      v-if="showLegend"
      class="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-t border-hairline bg-surface-sunken/40 text-caption font-sans"
    >
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-ink-muted text-[11px] font-medium">Entidades GraphRAG:</span>
        <div
          v-for="t in activeLegendTypes"
          :key="t"
          class="flex items-center gap-1.5 text-[11px]"
        >
          <span
            class="w-2.5 h-2.5 rounded-pill shrink-0"
            :style="{ backgroundColor: colorFor(t) }"
          ></span>
          <span class="text-ink font-medium">{{ GRAPH_TYPE_LABELS[t] || t }}</span>
        </div>
      </div>
      <div class="text-[11px] text-ink-muted italic">
        Arrastra nodos para reorganizar · Rueda para zoom · Clic para inspeccionar
      </div>
    </div>
  </div>
</template>
