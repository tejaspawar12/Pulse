/**
 * History Stack Navigator - Handles navigation from History list to Workout Detail, Progress & Trends, Insights (Phase 3).
 */
import React from 'react';
import { TouchableOpacity, Text, View, Platform } from 'react-native';
import { createStackNavigator } from '@react-navigation/stack';
import { HistoryScreen } from '../screens/HistoryScreen';
import { WorkoutDetailScreen } from '../screens/WorkoutDetailScreen';
import { ProgressTrendsScreen } from '../screens/ProgressTrendsScreen';
import { InsightsScreen } from '../screens/InsightsScreen';
import { isPortfolioMode } from '../config/constants';

const Stack = createStackNavigator();

const webContainerStyle = Platform.OS === 'web' ? { flex: 1, minHeight: '100vh', width: '100%' } : { flex: 1 };

export const HistoryStackNavigator: React.FC = () => {
  return (
    <View style={webContainerStyle}>
      <Stack.Navigator
        screenOptions={{
          headerShown: true,
          ...(Platform.OS === 'web' && { cardStyle: { flex: 1 } }),
        }}
      >
        <Stack.Screen
          name="HistoryList"
          component={HistoryScreen}
        options={({ navigation }) => ({
          title: 'History',
          headerRight: isPortfolioMode
            ? () => (
                <TouchableOpacity
                  onPress={() => navigation.navigate('Insights')}
                  style={{ marginRight: 8 }}
                >
                  <Text style={{ color: '#007AFF', fontSize: 16 }}>Insights</Text>
                </TouchableOpacity>
              )
            : undefined,
        })}
      />
      <Stack.Screen
        name="WorkoutDetail"
        component={WorkoutDetailScreen}
        options={{
          title: 'Workout Details',
        }}
      />
      <Stack.Screen
        name="ProgressTrends"
        component={ProgressTrendsScreen}
        options={{
          title: 'Progress & Trends',
        }}
      />
      <Stack.Screen
        name="Insights"
        component={InsightsScreen}
        options={{
          title: 'Insights',
        }}
      />
      </Stack.Navigator>
    </View>
  );
};
