<template>
  <div class="editable-field" :class="{ editing: editing }">
    <span class="ef-key mono">{{ label }}</span>
    <template v-if="editing">
      <input
        ref="input"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @blur="handleCommit"
        @keydown.enter="handleCommit"
        @keydown.esc="handleCancel"
        class="ef-input mono"
      />
    </template>
    <template v-else>
      <button 
        @click="startEdit" 
        class="ef-value mono" 
        :class="{ readonly: readOnly }"
        :style="{ color: color || 'var(--text)' }"
      >
        {{ value }}
      </button>
    </template>
    <span v-if="suffix" class="ef-suffix mono">{{ suffix }}</span>
  </div>
</template>

<script>
export default {
  name: 'EditableField',
  props: {
    label: String,
    value: [String, Number],
    modelValue: [String, Number],
    color: String,
    readOnly: Boolean,
    editing: Boolean,
    suffix: String
  },
  emits: ['update:modelValue', 'edit', 'commit', 'cancel'],
  methods: {
    startEdit() {
      if (this.readOnly) return;
      this.$emit('edit');
      this.$nextTick(() => {
        if (this.$refs.input) this.$refs.input.focus();
      });
    },
    handleCommit() {
      this.$emit('commit');
    },
    handleCancel() {
      this.$emit('cancel');
    }
  }
}
</script>

<style scoped>
.editable-field {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
  border-radius: 3px;
  background: transparent;
}
.editable-field.editing {
  background: color-mix(in oklab, var(--accent) 8%, transparent);
}
.ef-key {
  width: 96px;
  font-size: 11px;
  color: var(--text-mute);
}
.ef-input {
  flex: 1;
  background: var(--panel-3);
  border: 1px solid var(--accent);
  border-radius: 3px;
  color: var(--accent);
  padding: 2px 6px;
  font-size: 12px;
  outline: none;
  min-width: 0;
}
.ef-value {
  flex: 1;
  text-align: left;
  background: transparent;
  border: none;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  cursor: text;
  border-bottom: 1px dashed var(--line-2);
  min-width: 0;
  word-break: break-all;
}
.ef-value.readonly {
  cursor: default;
  border-bottom: none;
}
.ef-value:not(.readonly):hover {
  background: var(--panel-3);
}
.ef-suffix {
  font-size: 10px;
  color: var(--accent);
  margin-left: auto;
}
</style>
