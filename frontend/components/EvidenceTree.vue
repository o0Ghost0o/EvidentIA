<script setup lang="ts">
import { computed } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Card from "~/components/ui/Card.vue";

export interface TreeNode {
  tipo: string;
  id: string;
  label: string;
}
export interface TreeEdge {
  origen_tipo: string;
  origen_id: string;
  destino_tipo: string;
  destino_id: string;
  tipo: string;
}
export interface EvidenceTreeData {
  root: { tipo: string; id: string };
  nodes: TreeNode[];
  edges: TreeEdge[];
}

const props = defineProps<{ tree: EvidenceTreeData | null }>();

interface Branch {
  node: TreeNode;
  via: string | null;
  children: Branch[];
}

const branches = computed<Branch[]>(() => {
  if (!props.tree) return [];
  const byKey = new Map(props.tree.nodes.map((n) => [`${n.tipo}:${n.id}`, n]));
  const children = new Map<string, { edge: TreeEdge; node: TreeNode }[]>();
  for (const e of props.tree.edges) {
    const from = `${e.origen_tipo}:${e.origen_id}`;
    const to = `${e.destino_tipo}:${e.destino_id}`;
    const node = byKey.get(to);
    if (node) {
      if (!children.has(from)) children.set(from, []);
      children.get(from)!.push({ edge: e, node });
    }
  }
  const rootKey = `${props.tree.root.tipo}:${props.tree.root.id}`;
  const root = byKey.get(rootKey);
  if (!root) return [];
  const visited = new Set<string>([rootKey]);
  const build = (node: TreeNode, via: string | null): Branch => {
    const key = `${node.tipo}:${node.id}`;
    const kids: Branch[] = [];
    for (const { edge, node: child } of children.get(key) || []) {
      const ck = `${child.tipo}:${child.id}`;
      if (visited.has(ck)) continue;
      visited.add(ck);
      kids.push(build(child, edge.tipo));
    }
    return { node, via, children: kids };
  };
  return [build(root, null)];
});
</script>

<template>
  <Card>
    <template #header>Árbol de evidencia</template>
    <p v-if="!tree" class="text-sm text-muted-foreground">Sin árbol para mostrar.</p>
    <ul v-else class="text-sm">
      <TreeBranch v-for="(b, i) in branches" :key="i" :branch="b" />
    </ul>
  </Card>
</template>
