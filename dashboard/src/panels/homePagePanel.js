import PowerFrequencyPanel from "./PowerFrequencyPanel";
import SnapshotWaveformPanel from "./SnapshotWaveformPanel";
import WaveformStatisticsPanel from "./WaveformStatisticsPanel";

import Grid from "@material-ui/core/Grid";
import { makeStyles } from "@material-ui/core/styles";
import { useState } from "react";

const useStyles = makeStyles((theme) => ({
  root: {
    padding: 70,
  },
}));

const __frequencyRanges = [
  [16, 60, 'sub-bass', 'sb', '#F94144'],
  [60, 250, 'bass', 'b', '#F3722C'],
  [250, 500, 'low-mid', 'lm', '#F8961E'],
  [500, 2000, 'mid', 'm', '#F9C74F'],
  [2000, 4000, 'high-mid', 'hm', '#90BE6D'],
  [4000, 6000, 'low-high', 'lh', '#43AA8B'],
  [6000, 20000, 'high', 'h', '#577590'],
];

export default function HomePagePanel() {
  const classes = useStyles();
  const [waveform, setWaveform] = useState({});
  const [frequencyRanges, setFrequencyRanges] = useState(__frequencyRanges);

  return (
    <Grid container spacing={2} className={classes.root}>
      <Grid container xs={12}>
        {/* <WaveformStatisticsPanel
          waveform={waveform}
          frequencyRanges={frequencyRanges}
        /> */}
      </Grid>
      <Grid container xs={12}>
        <Grid container item xs={12} lg={6}>
          <PowerFrequencyPanel
            waveform={waveform}
            setWaveform={setWaveform}
            frequencyRanges={frequencyRanges}
          />
        </Grid>
        {/* <Grid container item xs={12} lg={6}>
          <SnapshotWaveformPanel
            waveform={waveform}
            frequencyRanges={frequencyRanges}
          />
        </Grid> */}
      </Grid>
    </Grid>
  );
}
