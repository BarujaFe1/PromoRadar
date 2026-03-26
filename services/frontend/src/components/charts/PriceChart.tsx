"use client";

import type { PriceHistoryPoint } from "@/types";
import { formatBRL, formatDateShort } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface PriceChartProps {
  data: PriceHistoryPoint[];
  minPrice?: number;
  height?: number;
}

export function PriceChart({ data, minPrice, height = 300 }: PriceChartProps) {
  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-sm text-surface-700/50 rounded-lg border border-dashed border-surface-200"
        style={{ height }}
      >
        Sem dados de histórico
      </div>
    );
  }

  const chartData = data.map((point) => ({
    ...point,
    date: formatDateShort(point.date),
    priceFormatted: formatBRL(point.price),
  }));

  const prices = data.map((p) => p.price);
  const yMin = Math.floor(Math.min(...prices) * 0.95);
  const yMax = Math.ceil(Math.max(...prices) * 1.05);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#64748b" }}
          tickLine={false}
          axisLine={{ stroke: "#e2e8f0" }}
        />
        <YAxis
          domain={[yMin, yMax]}
          tick={{ fontSize: 11, fill: "#64748b" }}
          tickFormatter={(v: number) => `R$${v}`}
          tickLine={false}
          axisLine={false}
          width={70}
        />
        <Tooltip
          contentStyle={{
            borderRadius: "8px",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            fontSize: "13px",
          }}
          formatter={(value: number) => [formatBRL(value), "Preço"]}
          labelFormatter={(label) => `Data: ${label}`}
        />
        {minPrice && (
          <ReferenceLine
            y={minPrice}
            stroke="#22c55e"
            strokeDasharray="5 5"
            label={{
              value: `Menor: ${formatBRL(minPrice)}`,
              position: "insideTopLeft",
              fill: "#16a34a",
              fontSize: 11,
            }}
          />
        )}
        <Line
          type="monotone"
          dataKey="price"
          stroke="#16a34a"
          strokeWidth={2.5}
          dot={{ fill: "#16a34a", r: 3, strokeWidth: 0 }}
          activeDot={{ fill: "#16a34a", r: 5, stroke: "#fff", strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
