<template><svg :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" :stroke-width="sw" stroke-linecap="round" stroke-linejoin="round"><path d="M3 15l3-4 3 2 3-6 3 4 2-2"/><path d="M3 17h14"/></svg></template>
<script>export default { name: 'IconLog', props: { size: { type: [Number,String], default: 18 }, sw: { type: [Number,String], default: 1.5 } } }</script>
