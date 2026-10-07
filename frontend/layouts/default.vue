<template>
  <div class="min-h-screen">
    <header class="border-b">
      <nav class="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
        <NuxtLink to="/" class="text-lg font-bold">EvidentIA</NuxtLink>
        <NuxtLink to="/" class="text-sm text-muted-foreground hover:text-foreground">Bandeja</NuxtLink>
        <NuxtLink to="/projects" class="text-sm text-muted-foreground hover:text-foreground">Proyectos</NuxtLink>
        <NuxtLink to="/ingest" class="text-sm text-muted-foreground hover:text-foreground">Ingesta</NuxtLink>
      </nav>
    </header>
    <main class="mx-auto max-w-5xl px-4 py-6">
      <slot />
    </main>
  </div>
</template>
