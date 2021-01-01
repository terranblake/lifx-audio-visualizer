import React from "react";
import moment from "moment";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

const CustomizedLabel = (props) => {
  const { x, y, stroke, value } = props;
  return (
    <text x={x} y={y} dy={-4} fill={stroke} fontSize={10} textAnchor={"middle"}>
      {value}
    </text>
  );
};

// replace the chart with this zoomable one from recharts
// https://codesandbox.io/s/l4pq6x00xq?file=/src/Hello.js

export default function SnapshotWaveformPanel(props) {
  const { waveform, frequencyRanges } = props;

  const getChartLines = () => {
    return (
      <Line
        type="monotone"
        name="power"
        dot={false}
        dataKey="power"
        key="power"
        label={<CustomizedLabel />}
      />
    );
  };

  const getReferencesLines = () => {
    return frequencyRanges.map((r) => {
      return (
        <ReferenceLine
          x={r[1]}
          key={r[2]}
          label={{
            value: r[2],
            angle: -90,
            position: "insideLeft",
            textAnchor: "middle",
          }}
          stroke="red"
          strokeDasharray="3 3"
        />
      );
    });
  };

  const getXAxisTicks = () => {
    const ticks = frequencyRanges.reduce(
      (acc, curr) => {
        acc.push(curr[0]);
        acc.push(curr[1]);
        return acc;
      },
      [0, 20000]
    );
    return ticks;
  };

  const getYAxisTicks = () => {
    return [0];
  };

  const renderTable = (data) => {
    return waveform ? (
      <LineChart
        width={1000}
        height={350}
        data={data}
        style={{ textAlign: "center" }}
        margin={{
          top: 0,
          right: 100,
          left: 100,
          bottom: 0,
        }}
      >
        <CartesianGrid strokeDasharray="1 1" />
        <XAxis dataKey="frequency" ticks={getXAxisTicks()} />
        <YAxis ticks={getYAxisTicks()} />
        {getReferencesLines()}
        <Tooltip />
        <Legend />
        {getChartLines()}
      </LineChart>
    ) : (
      <div>No snapshot set yet.</div>
    );
  };

  return <div>{renderTable(waveform)}</div>;
}
