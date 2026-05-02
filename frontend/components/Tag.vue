<template>
  <span class="tag mono" :style="{ background: bg, color: fg }">
    <slot />
  </span>
</template>

<script>
export default {
  name: 'Tag',
  props: {
    fg: { type: String, default: 'var(--text-dim)' },
    bg: { type: String, default: 'var(--panel-3)' }
  }
}
</script>

<style scoped>
.tag {
  display: inline-flex; align-items: center;
  font-size: 10.5px; padding: 2px 6px; border-radius: 3px;
  letter-spacing: 0.03em;
  border: 1px solid color-mix(in oklab, currentColor 15%, transparent);
}
</style>
