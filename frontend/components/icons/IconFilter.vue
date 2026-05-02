<template><svg :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" :stroke-width="sw" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h14l-5 7v5l-4-2v-3z"/></svg></template>
<script>export default { name: 'IconFilter', props: { size: { type: [Number,String], default: 18 }, sw: { type: [Number,String], default: 1.5 } } }</script>
