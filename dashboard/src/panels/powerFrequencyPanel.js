import React, { PureComponent } from "react";
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
  ReferenceArea,
} from "recharts";
import { getSocket, ENDPOINT } from "../utils/socketio";

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

export default class PowerFrequencyPanel extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      data: undefined,
      refAreaLeft: undefined,
      refAreaRight: undefined,
      subscription: {
        command: "microphone",
        arguments: {
          x: "frequency",
          y: "power",
        },
      },
      left: 0,
      right: 12000,
      top: 3,
      bottom: -3,
    };

    this.zoom = this.zoom.bind(this);
    this.zoomOut = this.zoomOut.bind(this);

    this.onOpen = this.onOpen.bind(this);
    this.onClose = this.onClose.bind(this);
    this.onMessage = this.onMessage.bind(this);

    this.getChartZones = this.getChartZones.bind(this);
    this.getChartLines = this.getChartLines.bind(this);
  }

  componentDidMount() {
    this.ws = getSocket(this.state.subscription.command);
    this.ws.onopen = this.onOpen;
    this.ws.onclose = this.onClose;
    this.ws.onmessage = this.onMessage;
  }

  onOpen(event) {
    console.debug("socket opened", event);
    this.ws.send(JSON.stringify(this.state.subscription));
  }

  onMessage(event) {
    // console.debug('socket received message', event);
    const data = JSON.parse(event.data);

    // fixme: new state should be handled using actions, reducers, sagas, etc.

    let formattedData = [];
    const multiplier =
      Math.pow(Math.max(...data.data.power), -1) * (this.state.top * 0.8);
    for (let i = 0; i < data.data.frequency.length; i++) {
      formattedData.push({
        frequency: data.data.frequency[i],
        power: data.data.power[i] * multiplier,
      });
    }

    const streamReadAt = data.data.streamReadAt;
    this.props.setWaveform({
      ...(streamReadAt && { streamReadAt }),
      data: formattedData,
    });

    this.setState({ data: formattedData.slice() });
  }

  onClose(event) {
    console.debug("socket closed", event);
  }

  getAxisYDomain(from, to, ref, offset) {
    const refData = this.state.data.slice(from - 1, to);
    if (!refData.length) return [this.state.bottom, this.state.top];

    let [bottom, top] = [refData[0][ref], refData[0][ref]];
    refData.forEach((d) => {
      if (d[ref] > top) top = d[ref];
      if (d[ref] < bottom) bottom = d[ref];
    });

    return [(bottom | 0) - offset, (top | 0) + offset];
  }

  getChartLines() {
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
  }

  getChartZones() {
    return this.props.frequencyRanges.map((r) => (
      <ReferenceArea
        x1={r[0]}
        x2={r[1]}
        y1={-3}
        y2={0}
        key={r[0]}
        stroke={r[3]}
        strokeOpacity={0.1}
      />
    ));
  }

  getReferencesLines() {
    return this.props.frequencyRanges.map((r) => {
      return (
        <ReferenceLine
          x={r[1]}
          key={r[2]}
          label={{
            value: r[2],
            angle: -45,
            position: "middle",
            textAnchor: "middle",
            fontSize: 10,
            fill: "rgba(0, 255, 0, 1.0)",
          }}
          stroke="red"
          strokeDasharray="3 3"
          //   yAxisId={r[2]}
        />
      );
    });
  }

  getXAxisTicks() {
    const { left, right } = this.state;
    const ticks = this.props.frequencyRanges.reduce(
      (acc, curr) => {
        if (curr[0] >= left && curr[0] <= right) acc.push(curr[0]);

        if (curr[1] >= left && curr[1] <= right) acc.push(curr[1]);
        return acc;
      },
      [this.state.right]
    );
    return ticks;
  }

  getYAxisTicks() {
    return [this.state.bottom, this.state.top];
  }

  zoom() {
    let { refAreaLeft, refAreaRight, data } = this.state;

    if (!data || !data.length) {
      console.log("missing data when zooming");
      return;
    }

    console.log("zooming", { refAreaLeft, refAreaRight, data });

    if (refAreaLeft === refAreaRight || refAreaRight === "") {
      this.setState({
        refAreaLeft: "",
        refAreaRight: "",
      });
      return;
    }

    // xAxis domain
    if (refAreaLeft > refAreaRight)
      [refAreaLeft, refAreaRight] = [refAreaRight, refAreaLeft];

    // yAxis domain
    const [bottom, top] = this.getAxisYDomain(
      refAreaLeft,
      refAreaRight,
      "power",
      1
    );

    this.setState({
      refAreaLeft: "",
      refAreaRight: "",
      data: data.slice(),
      left: refAreaLeft,
      right: refAreaRight,
      bottom,
      top,
    });
  }

  zoomOut() {
    const { data } = this.state;
    console.debug("zooming out");
    this.setState({
      data: data.slice(),
      refAreaLeft: 0,
      refAreaRight: 0,
      left: 0,
      right: 12000,
      top: 1,
      bottom: -1,
    });
  }

  render() {
    const {
      left,
      right,
      top,
      bottom,
      refAreaLeft,
      refAreaRight,
      data,
    } = this.state;
    return (
      <div>
        {!data || !data.length ? (
          <div>No data found at {ENDPOINT}...</div>
        ) : (
          <div style={{ textAlign: "center" }}>
            <button className="btn update" onClick={this.zoomOut.bind(this)}>
              Zoom Out
            </button>
            <LineChart
              data={data}
              margin={{
                top: 20,
                right: 50,
                left: 50,
                bottom: 20,
              }}
              width={1200}
              height={400}
              onMouseDown={(e) =>
                e && this.setState({ refAreaLeft: e.activeLabel })
              }
              onMouseMove={(e) =>
                refAreaLeft &&
                e &&
                this.setState({ refAreaRight: e.activeLabel })
              }
              onMouseUp={this.zoom.bind(this)}
            >
              <CartesianGrid strokeDasharray="1 1" />
              <XAxis
                allowDataOverflow={true}
                dataKey="frequency"
                type="number"
                ticks={this.getXAxisTicks()}
                domain={[left, right]}
              />
              <YAxis
                domain={[bottom, top]}
                allowDataOverflow={true}
                dataKey="power"
              />
              {this.getReferencesLines()}
              <Tooltip />
              <Legend />
              {this.getChartLines()}
              {/* {this.getChartZones()} */}
              <Tooltip />
              {refAreaLeft && refAreaRight ? (
                <ReferenceArea
                  //   yAxisId="1"
                  x1={refAreaLeft}
                  x2={refAreaRight}
                  strokeOpacity={0.3}
                  //   key="selection"
                />
              ) : null}
            </LineChart>
            {/* <div className="input-field">
              <p>
                {moment
                  .unix(this.props.waveform.streamReadAt)
                  .format("MM/DD/YY HH:mm:ss") || ""}
              </p>
            </div> */}
          </div>
        )}
      </div>
    );
  }
}
