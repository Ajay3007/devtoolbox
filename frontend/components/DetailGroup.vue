<template>
  <div class="detail-group" :class="{ highlight: highlight }">
    <button @click="open = !open" class="dg-toggle">
      <IconChevD v-if="open" :size="12" />
      <IconChevR v-else :size="12" />
      <span class="dg-label">{{ label }}</span>
    </button>
    <div v-if="open" class="dg-body">
      <slot></slot>
    </div>
  </div>
</template>

<script>
import { IconChevR, IconChevD } from './icons'

export default {
  name: 'DetailGroup',
  components: { IconChevR, IconChevD },
  props: {
    label: String,
    expanded: Boolean,
    highlight: Boolean
  },
  data() {
    return {
      open: this.expanded || false
    }
  }
}
</script>

<style scoped>
.detail-group {
  border: 1px solid var(--line);
  border-left: 1px solid var(--line);
  border-radius: 5px;
  margin-bottom: 8px;
  background: var(--panel-2);
  overflow: hidden;
}
.detail-group.highlight {
  border-left: 2px solid var(--accent-4);
}
.dg-toggle {
  width: 100%;
  background: transparent;
  border: none;
  padding: 7px 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 11.5px;
  letter-spacing: 0.08em;
  cursor: pointer;
  text-align: left;
}
.dg-toggle:hover {
  background: color-mix(in oklab, var(--line) 30%, transparent);
}
.dg-label {
  text-transform: uppercase;
}
.dg-body {
  padding: 4px 8px 8px;
}
</style>
