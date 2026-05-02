<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M4 2h16v20l-2-1.5L16 22l-2-1.5L12 22l-2-1.5L8 22l-2-1.5L4 22V2z"/>
    <line x1="8" y1="8"  x2="16" y2="8"/>
    <line x1="8" y1="12" x2="16" y2="12"/>
    <line x1="8" y1="16" x2="12" y2="16"/>
  </svg>
</template>
<script>
export default { props: { size: { default: 16 } } }
</script>
