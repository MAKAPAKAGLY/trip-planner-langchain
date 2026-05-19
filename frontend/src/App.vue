<template>
  <a-config-provider :theme="themeConfig">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
const themeConfig = {
  token: {
    colorPrimary: '#c8963e',
    colorSuccess: '#5b8c5a',
    colorWarning: '#d4a853',
    colorError: '#c05a4a',
    colorInfo: '#4a7c96',
    borderRadius: 10,
    fontFamily: "'DM Sans', 'Noto Sans SC', -apple-system, sans-serif",
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBorderSecondary: '#e8e2d8',
    colorText: '#2c2416',
    colorTextSecondary: '#8b7e74',
    controlHeightLG: 48,
  },
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'DM Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c2416;
  background: #faf8f4;
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(200, 150, 62, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(74, 124, 150, 0.03) 0%, transparent 50%);
  min-height: 100vh;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d4cdc0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #b8afa0; }

.ant-card { border-color: #e8e2d8 !important; }
.ant-input, .ant-input-number, .ant-picker, .ant-select-selector { border-color: #d4cdc0 !important; }
.ant-input:hover, .ant-input-number:hover, .ant-picker:hover, .ant-select:hover .ant-select-selector { border-color: #c8963e !important; }
.ant-input:focus, .ant-input-number:focus, .ant-picker:focus, .ant-select-focused .ant-select-selector {
  border-color: #c8963e !important;
  box-shadow: 0 0 0 2px rgba(200, 150, 62, 0.12) !important;
}
.ant-btn-primary { background: #1a2942 !important; border-color: #1a2942 !important; box-shadow: 0 2px 8px rgba(26, 41, 66, 0.2) !important; }
.ant-btn-primary:hover { background: #243556 !important; border-color: #243556 !important; box-shadow: 0 4px 16px rgba(26, 41, 66, 0.3) !important; }
.ant-collapse-header { font-family: 'Noto Sans SC', sans-serif; }
.ant-tag { border-radius: 6px; }
</style>
