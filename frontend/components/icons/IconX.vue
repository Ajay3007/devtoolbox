<template><svg :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" :stroke-width="sw" stroke-linecap="round" stroke-linejoin="round"><path d="m5 5 10 10M15 5 5 15"/></svg></template>
<script>export default { name: 'IconX', props: { size: { type: [Number,String], default: 18 }, sw: { type: [Number,String], default: 1.5 } } }</script>
