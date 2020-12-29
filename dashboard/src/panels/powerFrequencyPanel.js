import React, { PureComponent } from 'react';
import moment from 'moment';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';

import { getSocket, ENDPOINT } from '../utils/socketio';


// replace the chart with this zoomable one from recharts
// https://codesandbox.io/s/l4pq6x00xq?file=/src/Hello.js

export default class PowerFrequencyPanel extends PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            formattedData: [],
            subscription: {
                command: 'microphone',
                arguments: {
                    x: 'frequency',
                    y: 'power'
                }
            },
        };

        this.onOpen = this.onOpen.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onMessage = this.onMessage.bind(this);
        this.getChartLines = this.getChartLines.bind(this);
    }

    componentDidMount() {
        this.ws = getSocket(this.state.subscription.command);
        this.ws.onopen = this.onOpen;
        this.ws.onclose = this.onClose;
        this.ws.onmessage = this.onMessage;
    }

    onOpen(event) {
        console.log('socket opened', event);
        this.ws.send(JSON.stringify(this.state.subscription));
    }

    onMessage(event) {
        const data = JSON.parse(event.data);
        // console.log('socket received data', data);

        let formattedData = [];
        for (let i = 0; i < data.data.frequency.length; i++) {
            formattedData.push({
                frequency: data.data.frequency[i],
                power: data.data.power[i]
            });
        }

        this.setState({
            time: data.data.time,
            data: formattedData
        });
    }

    onClose(event) {
        console.log('socket closed', event);
    }

    getChartLines() {
        return <Line
            type="monotone"
            name='power'
            dot={false}
            dataKey="power"
            key='power'
        />;
    }

    render() {
        return (
            <div>
                {
                    !this.state.data.length
                        ? <div>No data found at {ENDPOINT}...</div>
                        :
                        <div style={{ textAlign: 'center' }}>
                            <div className="input-field">
                                <input type="text" name="name" ref="name" value={moment.unix(this.state.time).format("MM/DD/YYYY HH:mm:ss") || ''} />
                                <label htmlFor="name">Name</label>
                            </div>
                            <LineChart
                                width={600}
                                height={350}
                                data={this.state.data}
                                margin={{
                                    top: 0, right: 0, left: 0, bottom: 0,
                                }}
                            >
                                <CartesianGrid strokeDasharray="1 1" />
                                <XAxis dataKey="frequency" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                {this.getChartLines()}
                            </LineChart>
                        </div>

                }
            </div>
        );
    }
}
