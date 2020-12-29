import React, { PureComponent } from 'react';
import moment from 'moment';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';

import { getSocket } from '../utils/socketio';


// replace the chart with this zoomable one from recharts
// https://codesandbox.io/s/l4pq6x00xq?file=/src/Hello.js

export default class PowerFrequencyPanel extends PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            formattedData: [],
            subscription: {
                command: 'frequency',
                arguments: {
                }
            },
        };

        this.onOpen = this.onOpen.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onMessage = this.onMessage.bind(this);
        this.getChartLines = this.getChartLines.bind(this);
        this.getFormattedData = this.getFormattedData.bind(this);
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
        console.log('socket received data', data);

        this.setState({ data }, this.getFormattedData());
    }

    onClose(event) {
        console.log('socket closed', event);
    }

    getFormattedData() {
        // const historyByDate = this.state.data.reduce((acc, curr) => {
        //     // this.state.fields.forEach(f => {
        //     if ('symbol' in curr)
        //         acc[curr['date']] = {
        //             [`${this.state.selectedField}_${curr['symbol'].toLowerCase()}`]: curr[this.state.selectedField],
        //             ...acc[curr['date']]
        //         };
        //     // });

        //     return acc;
        // }, {});

        // const formattedData = Object.keys(historyByDate).map(k => {
        //     return { date: k, ...historyByDate[k] };
        // });
        const formattedData = this.state.data;

        console.log({ formattedData });
        this.setState({ formattedData });
    }

    getChartLines() {
        return <Line
            type="monotone"
            name='amplitude'
            dot={false}
            dataKey="amplitude"
            key='amplitude'
        />;
    }

    render() {
        return (
            <div>
                {
                    !this.state.data.length
                        ? <div>no data found</div>
                        :
                        <div style={{ textAlign: 'center' }}>
                            <LineChart
                                width={600}
                                height={350}
                                data={this.state.formattedData}
                                margin={{
                                    top: 0, right: 0, left: 0, bottom: 0,
                                }}
                            >
                                <CartesianGrid strokeDasharray="1 1" />
                                <XAxis dataKey="power" />
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
