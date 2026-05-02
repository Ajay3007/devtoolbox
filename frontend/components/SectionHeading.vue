<template>
  <div class="section-heading">
    <div v-if="kicker" class="mono kicker">{{ kicker }}</div>
    <h2 class="heading-title">{{ title }}</h2>
    <p v-if="desc" class="heading-desc">{{ desc }}</p>
    <slot />
  </div>
</template>

<script>
export default {
  name: 'SectionHeading',
  props: {
    kicker: String,
    title: { type: String, required: true },
    desc: String
  }
}
</script>

<style scoped>
.section-heading { margin-bottom: 18px; }
.kicker {
  font-size: 11px; color: var(--accent);
  letter-spacing: 0.15em; margin-bottom: 8px;
}
.heading-title {
  font-size: 26px; font-weight: 700;
  letter-spacing: -0.02em; margin: 0;
}
.heading-desc {
  font-size: 14px; color: var(--text-dim);
  margin: 8px 0 0; max-width: 720px;
}
</style>
