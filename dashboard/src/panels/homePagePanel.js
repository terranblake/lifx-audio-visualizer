import PowerFrequencyPanel from './powerFrequencyPanel';

import Grid from '@material-ui/core/Grid';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
    root: {
        padding: 30,
    },
}));

export default function HomePagePanel() {
    const classes = useStyles();

    return (
        <Grid container spacing={2} className={classes.root}>
            <Grid container xs={12}>
                <Grid container item xs={12} lg={12}>
                    <PowerFrequencyPanel />
                </Grid>
            </Grid>
        </Grid>
    )
}