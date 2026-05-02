<template><svg :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" :stroke-width="sw" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="9" r="5"/><path d="m13 13 4 4"/></svg></template>
<script>export default { name: 'IconSearch', props: { size: { type: [Number,String], default: 18 }, sw: { type: [Number,String], default: 1.5 } } }</script>
