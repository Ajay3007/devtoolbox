<template>
  <div>
    <div class="field-label mono">
      {{ label.toUpperCase() }}
      <span v-if="suffix" class="field-suffix" :style="{ color: suffixColor || 'var(--text-mute)' }">
        {{ suffix }}
      </span>
    </div>
    <div class="field-input-wrapper">
      <input
        :type="type || 'text'"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        class="field-input mono"
        :style="{ color: color || 'var(--text)' }"
        :placeholder="placeholder"
        :disabled="disabled"
        :min="min"
        :max="max"
        :maxlength="maxlength"
      />
      <slot name="picker"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Field',
  props: {
    label: String,
    modelValue: [String, Number],
    type: String,
    suffix: String,
    suffixColor: String,
    color: String,
    placeholder: String,
    disabled: Boolean,
    min: [String, Number],
    max: [String, Number],
    maxlength: [String, Number]
  },
  emits: ['update:modelValue']
}
</script>

<style scoped>
.field-label {
  font-size: 10.5px;
  color: var(--text-mute);
  margin-bottom: 4px;
  letter-spacing: 0.1em;
}
.field-suffix {
  margin-left: 6px;
  text-transform: none;
  letter-spacing: 0;
}
.field-input-wrapper {
  position: relative;
  display: flex;
}
.field-input {
  width: 100%;
  padding: 8px 10px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  font-size: 12.5px;
  font-family: var(--mono);
  outline: none;
  box-sizing: border-box;
}
.field-input:focus {
  border-color: var(--accent);
}
.field-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
