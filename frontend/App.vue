<template>
  <div id="app" class="app-shell">
    <LeftRail />
    <div class="app-content">
      <TopBar />
      <main class="app-main">
        <div class="view-animate" :key="$route.path">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import LeftRail from './components/LeftRail.vue'
import TopBar from './components/TopBar.vue'

export default {
  name: 'App',
  components: { LeftRail, TopBar }
}
</script>

<style>
/* Shell layout — unscoped so child views inherit tokens */
.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-content {
  margin-left: 232px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.view-animate {
  animation: slideIn 0.3s ease-out;
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
