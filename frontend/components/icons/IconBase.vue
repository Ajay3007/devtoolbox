<!-- Base Icon wrapper - not used directly, icons inline their SVGs -->
<template>
  <svg :width="size" :height="size" viewBox="0 0 20 20" fill="none"
       stroke="currentColor" :stroke-width="strokeWidth" stroke-linecap="round" stroke-linejoin="round">
    <slot />
  </svg>
</template>

<script>
export default {
  name: 'IconBase',
  props: {
    size: { type: [Number, String], default: 18 },
    strokeWidth: { type: [Number, String], default: 1.5 }
  }
}
</script>
