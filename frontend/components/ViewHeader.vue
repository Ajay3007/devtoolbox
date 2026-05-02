<template>
  <div class="view-header">
    <div class="vh-main">
      <div class="vh-icon-wrap">
        <component :is="icon" :size="18"/>
      </div>
      <div>
        <h1 class="vh-title">{{ title }}</h1>
        <p class="vh-subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <div class="vh-actions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ViewHeader',
  props: ['icon', 'title', 'subtitle']
}
</script>

<style scoped>
.view-header {
  padding: 20px 28px 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}
.vh-main {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}
.vh-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 7px;
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  border: 1px solid color-mix(in oklab, var(--accent) 25%, transparent);
  color: var(--accent);
  display: grid;
  place-items: center;
}
.vh-title {
  font-size: 22px;
  margin: 0;
  letter-spacing: -0.01em;
  font-weight: 700;
  color: var(--text);
}
.vh-subtitle {
  font-size: 13px;
  color: var(--text-dim);
  margin: 2px 0 0;
  max-width: 640px;
  line-height: 1.4;
}
.vh-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
:deep(.vh-actions .btn) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
:deep(.vh-actions .btn-primary) {
  background: var(--accent);
  color: #0b0d10;
  border: none;
}
:deep(.vh-actions .btn-primary:hover) {
  filter: brightness(1.1);
}
:deep(.vh-actions .btn-ghost) {
  background: transparent;
  color: var(--text-dim);
  border: 1px solid var(--line-2);
}
:deep(.vh-actions .btn-ghost:hover) {
  background: var(--panel-2);
  color: var(--text);
}
</style>
