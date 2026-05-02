<template>
  <div class="code-block">
    <div class="code-title mono">
      $ {{ title }}
    </div>
    <div class="code-lines mono">
      <div v-for="(l, i) in lines" :key="i">
        <div><span style="color: var(--accent)">$</span> <span>{{ l.c }}</span></div>
        <div v-if="l.out" style="color: var(--text-mute)">  {{ l.out }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CodeBlock',
  props: {
    title: { type: String, required: true },
    lines: { type: Array, required: true }
  }
}
</script>

<style scoped>
.code-block {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
}
.code-title {
  padding: 7px 12px; font-size: 11.5px;
  color: var(--text-dim);
  border-bottom: 1px solid var(--line);
  background: var(--panel-2);
}
.code-lines {
  padding: 12px;
  font-size: 12px; line-height: 1.65;
}
</style>
