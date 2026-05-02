<template>
  <section class="panel" :style="style">
    <header v-if="title || $slots.right" class="panel-header">
      <div>
        <div v-if="title" class="panel-title">{{ title }}</div>
        <div v-if="subtitle" class="panel-subtitle">{{ subtitle }}</div>
      </div>
      <slot name="right" />
    </header>
    <div class="panel-body" :style="{ padding: padding + 'px' }">
      <slot />
    </div>
  </section>
</template>

<script>
export default {
  name: 'Panel',
  props: {
    title: String,
    subtitle: String,
    padding: { type: Number, default: 16 },
    style: Object
  }
}
</script>

<style scoped>
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 14px;
  border-bottom: 1px solid var(--line);
  background: var(--panel-2);
}
.panel-title { font-size: 13px; font-weight: 600; }
.panel-subtitle { font-size: 11.5px; color: var(--text-dim); margin-top: 1px; }
</style>
