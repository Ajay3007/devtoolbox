<template>
  <div class="flow-diagram">
    <div v-for="(step, i) in steps" :key="i" class="flow-step">
      <span class="mono flow-index">{{ String(i + 1).padStart(2, '0') }}</span>
      <span class="flow-dot" :style="{ background: step[1] }"></span>
      <span class="mono flow-label" :style="{ color: step[1] }">{{ step[0] }}</span>
      <span class="flow-line" :style="{ background: `color-mix(in oklab, ${step[1]} 20%, transparent)` }"></span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FlowDiagram',
  props: {
    proto: String
  },
  computed: {
    steps() {
      const flows = {
        tcp:  [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['ACK','var(--text-dim)'],['PSH-ACK','var(--accent-4)'],['ACK','var(--text-dim)'],['FIN-ACK','var(--accent-3)']],
        http: [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['ACK','var(--text-dim)'],['GET','var(--accent-3)'],['200 OK','var(--accent-3)'],['ACK','var(--text-dim)'],['FIN-ACK','var(--accent-3)'],['ACK','var(--text-dim)']],
        tls:  [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['ACK','var(--text-dim)'],['Client Hello','var(--accent-4)'],['Server Hello','var(--accent-4)'],['Certificate','var(--accent-4)'],['Finished','var(--accent-4)'],['ACK','var(--text-dim)']],
        dns_udp: [['Query','var(--accent-5)'],['Response','var(--accent-5)']],
        dns_tcp: [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['Query','var(--accent-5)'],['Response','var(--accent-5)']],
        udp: [['Datagram','var(--accent-2)']],
        icmp: [['Echo Request','var(--text-dim)'],['Echo Reply','var(--text-dim)']],
        arp: [['Who-Has','var(--text-dim)']],
      }
      return flows[this.proto] || []
    }
  }
}
</script>

<style scoped>
.flow-diagram {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.flow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 3px 4px;
}
.flow-index {
  font-size: 10.5px;
  color: var(--text-mute);
  width: 24px;
}
.flow-dot {
  width: 7px;
  height: 7px;
  border-radius: 7px;
}
.flow-label {
  font-size: 12px;
}
.flow-line {
  flex: 1;
  height: 1px;
}
</style>
