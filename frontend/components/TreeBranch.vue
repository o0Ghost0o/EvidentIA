<script setup lang="ts">
import Badge from "~/components/ui/Badge.vue";

interface Branch {
  node: { tipo: string; id: string; label: string };
  via: string | null;
  children: Branch[];
}

defineProps<{ branch: Branch }>();
</script>

<template>
  <li class="ml-3 border-l pl-3 py-1">
    <div class="flex flex-wrap items-center gap-2">
      <Badge variant="secondary">{{ branch.node.tipo }}</Badge>
      <span class="font-medium">{{ branch.node.label }}</span>
      <span v-if="branch.via" class="text-xs text-muted-foreground">← {{ branch.via }}</span>
    </div>
    <ul v-if="branch.children.length">
      <TreeBranch v-for="(c, i) in branch.children" :key="i" :branch="c" />
    </ul>
  </li>
</template>
