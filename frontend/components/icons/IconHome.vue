<template><svg :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" :stroke-width="sw" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9 10 3l7 6"/><path d="M5 8v9h10V8"/></svg></template>
<script>export default { name: 'IconHome', props: { size: { type: [Number,String], default: 18 }, sw: { type: [Number,String], default: 1.5 } } }</script>
