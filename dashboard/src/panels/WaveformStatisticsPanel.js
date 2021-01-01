import React, { useState } from "react";
import moment from "moment";
import {} from "recharts";

export default function WaveformStatisticsPanel(props) {
  const { waveform = {}, frequencyRanges } = props;
  const { streamReadAt } = waveform;
  const now = moment().format('x');

  return (
    <div>
      <p>{`current delay (ms)\t${now - streamReadAt}`}</p>
    </div>
  );
}
