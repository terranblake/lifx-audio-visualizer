import "date-fns";
import React, { useState } from "react";
import Grid from "@material-ui/core/Grid";
import DateFnsUtils from "@date-io/date-fns";
import {
    MuiPickersUtilsProvider,
    KeyboardDatePicker
} from "@material-ui/pickers";

export default function MaterialUIPickers() {
    // The first commit of Material-UI
    const [startDate, setStartDate] = useState(new Date("2014-08-18T21:11:54"));
    const [endDate, setEndDate] = useState(new Date("2014-08-18T21:11:54"));

    return (
        <MuiPickersUtilsProvider utils={DateFnsUtils}>
            <Grid container xs={12}>
                <Grid container item xs={12} lg={5}>
                    <KeyboardDatePicker
                        disableToolbar
                        variant="inline"
                        format="MM/dd/yyyy"
                        margin="normal"
                        id="date-picker-start"
                        label="Start date"
                        value={startDate}
                        onChange={setStartDate}
                        KeyboardButtonProps={{
                            "aria-label": "change start date"
                        }}
                    />
                </Grid>
                <Grid container item xs={12} lg={1}></Grid>
                <Grid container item xs={12} lg={5}>
                    <KeyboardDatePicker
                        margin="normal"
                        id="date-picker-end"
                        label="End date"
                        format="MM/dd/yyyy"
                        value={endDate}
                        onChange={setEndDate}
                        KeyboardButtonProps={{
                            "aria-label": "change end date"
                        }}
                    />
                </Grid>
                <Grid container item xs={12} lg={1}></Grid>
            </Grid>
        </MuiPickersUtilsProvider>
    );
}
