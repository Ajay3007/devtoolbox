<template>
  <div class="mini-stat">
    <div class="ms-label mono">{{ label.toUpperCase() }}</div>
    <div class="ms-value mono" :style="{ color: color || 'var(--text)' }">{{ value }}</div>
  </div>
</template>

<script>
export default {
  name: 'MiniStat',
  props: {
    label: String,
    value: [String, Number],
    color: String
  }
}
</script>

<style scoped>
.mini-stat {
  padding: 10px 12px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.ms-label {
  font-size: 10px;
  color: var(--text-mute);
  letter-spacing: 0.1em;
  margin-bottom: 4px;
}
.ms-value {
  font-size: 16px;
  font-weight: 600;
}
</style>
