/**
 * Volume chart using react-native-chart-kit (LineChart). Shows volume over time.
 */
import React, { useMemo } from 'react';
import { View, Text, StyleSheet, useWindowDimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import type { VolumeDataPoint } from '../../services/api/stats.api';
import { convertWeightForDisplay, getUnitLabel } from '../../utils/units';
import { parseLocalYMD, formatMonthDay } from '../../utils/date';

interface ProgressChartProps {
  data: VolumeDataPoint[];
  periodDays: number;
  units?: 'kg' | 'lb';
}

const chartConfig = {
  backgroundColor: '#fff',
  backgroundGradientFrom: '#fff',
  backgroundGradientTo: '#fff',
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 12,
    paddingRight: 16,
  },
  propsForLabels: {
    fontSize: 10,
  },
};

export const ProgressChart: React.FC<ProgressChartProps> = ({
  data,
  periodDays,
  units = 'kg',
}) => {
  const { width } = useWindowDimensions();
  const chartWidth = Math.max(width - 48, 280);

  const { labels, values } = useMemo(() => {
    if (!data.length) {
      return { labels: [''], values: [0] };
    }
    const rawValues = data.map((d) => d.total_volume_kg);
    const converted = rawValues.map((kg) =>
      convertWeightForDisplay(kg, units) ?? 0
    );
    const labels = data.map((d) => {
      const date = parseLocalYMD(d.period_start);
      return formatMonthDay(date);
    });
    // Show every Nth label to avoid overlap (e.g. 7 days → all; 30/90 → every 2nd or 3rd)
    const step = data.length <= 7 ? 1 : data.length <= 14 ? 2 : Math.ceil(data.length / 7);
    const spacedLabels = labels.map((l, i) => (i % step === 0 ? l : ''));
    return { labels: spacedLabels, values: converted };
  }, [data, units]);

  const hasAnyVolume = values.some((v) => v > 0);
  const displayValues = hasAnyVolume ? values : values.map(() => 0.1);

  if (!data.length) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Volume over time</Text>
        <View style={styles.placeholder}>
          <Text style={styles.placeholderText}>No volume data for this period</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Volume over time ({getUnitLabel(units)})</Text>
      <LineChart
        data={{
          labels,
          datasets: [{ data: displayValues }],
        }}
        width={chartWidth}
        height={200}
        chartConfig={chartConfig}
        bezier
        withInnerLines
        withOuterLines
        fromZero
        style={styles.chart}
        formatYLabel={(y) => {
          const n = Number(y);
          return Number.isFinite(n) ? (n >= 1 ? Math.round(n).toString() : '') : y;
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  chart: {
    borderRadius: 8,
  },
  placeholder: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 14,
    color: '#666',
  },
});
