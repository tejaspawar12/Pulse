const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Force zustand (and subpaths) to use CJS build on WEB ONLY so we avoid import.meta in the web bundle.
// Native (Expo Go) uses default resolution. The ESM build uses import.meta.env which breaks web when not loaded as type="module".
const defaultResolve = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web' && (moduleName === 'zustand' || moduleName.startsWith('zustand/'))) {
    const subpath = moduleName === 'zustand' ? 'index.js' : moduleName.replace('zustand/', '') + '.js';
    const filePath = path.join(__dirname, 'node_modules', 'zustand', subpath);
    return { type: 'sourceFile', filePath };
  }
  return defaultResolve ? defaultResolve(context, moduleName, platform) : context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
