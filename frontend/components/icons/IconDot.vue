<template><svg :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" :stroke-width="sw" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="2.2" fill="currentColor"/></svg></template>
<script>export default { name: 'IconDot', props: { size: { type: [Number,String], default: 18 }, sw: { type: [Number,String], default: 1.5 } } }</script>
