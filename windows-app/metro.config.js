/**
 * Metro configuration for React Native Windows.
 * `.md` files are bundled as assets so the app can also read raw
 * notes if a future release adds a "choose brain folder" picker.
 */
const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

const config = {
  resolver: {
    assetExts: [...getDefaultConfig(__dirname).resolver.assetExts, 'md'],
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
