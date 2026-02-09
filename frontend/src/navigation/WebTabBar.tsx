/**
 * Custom bottom tab bar for web (mobile and laptop).
 * Fixes: tabs hard to tap on mobile web, labels cut in half.
 * Uses large touch targets, full-height bar, and reliable click handling.
 */
import React, { useEffect } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { CommonActions } from '@react-navigation/native';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { getLabel } from '@react-navigation/elements';
import { BottomTabBarHeightCallbackContext } from '@react-navigation/bottom-tabs';

const TAB_BAR_HEIGHT = 72;
const ACTIVE_COLOR = '#007AFF';
const INACTIVE_COLOR = '#6b7280';

export function WebTabBar({ state, descriptors, navigation, insets }: BottomTabBarProps) {
  const { routes } = state;
  const paddingBottom = Math.max(insets?.bottom ?? 0, 12);
  const totalHeight = TAB_BAR_HEIGHT + paddingBottom;
  const setTabBarHeight = React.useContext(BottomTabBarHeightCallbackContext);

  useEffect(() => {
    setTabBarHeight?.(totalHeight);
    return () => setTabBarHeight?.(0);
  }, [totalHeight, setTabBarHeight]);

  return (
    <View
      style={[
        styles.container,
        { paddingBottom, height: TAB_BAR_HEIGHT + paddingBottom },
      ]}
      pointerEvents="box-none"
    >
      <View style={styles.bar} pointerEvents="auto">
        {routes.map((route, index) => {
          const focused = index === state.index;
          const { options } = descriptors[route.key];
          const label =
            typeof options.tabBarLabel === 'function'
              ? options.tabBarLabel
              : getLabel(
                  { label: options.tabBarLabel, title: options.title },
                  route.name
                );
          const labelText = typeof label === 'string' ? label : route.name;

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });
            if (!focused && !event.defaultPrevented) {
              navigation.dispatch({
                ...CommonActions.navigate(route),
                target: state.key,
              });
            }
          };

          const IconComponent = options.tabBarIcon;
          const color = focused ? ACTIVE_COLOR : INACTIVE_COLOR;

          return (
            <Pressable
              key={route.key}
              onPress={onPress}
              style={({ pressed }) => [
                styles.tab,
                pressed && styles.tabPressed,
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: focused }}
            >
              <View style={styles.iconWrap}>
                {IconComponent ? (
                  <IconComponent
                    focused={focused}
                    color={color}
                    size={24}
                  />
                ) : (
                  <Text style={styles.iconPlaceholder}>•</Text>
                )}
              </View>
              <Text
                style={[styles.label, { color }]}
                numberOfLines={1}
                allowFontScaling
              >
                {labelText}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    backgroundColor: '#fff',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#e5e7eb',
    justifyContent: 'flex-end',
    zIndex: 9999,
  },
  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    height: TAB_BAR_HEIGHT,
    paddingHorizontal: 8,
  },
  tab: {
    flex: 1,
    minHeight: 56,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 4,
    cursor: 'pointer',
  },
  tabPressed: {
    opacity: 0.7,
  },
  iconWrap: {
    marginBottom: 4,
    minHeight: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconPlaceholder: {
    fontSize: 20,
    color: '#9ca3af',
  },
  label: {
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'center',
  },
});
