import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Paper from "@material-ui/core/Paper";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

export default function StaticTable(props) {
  const classes = useStyles();
  const { stats = {} } = props;

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="static table">
        <TableHead>
          <TableRow>
            {stats[0].map((col, j) =>
              j == 0 ? (
                <TableCell component="th" scope="row">
                  {col}
                </TableCell>
              ) : (
                <TableCell align="right">{col}</TableCell>
              )
            )}
          </TableRow>
        </TableHead>
        <TableBody>
          {stats.map((row, i) => (
            <TableRow key={i}>
              {row.map((col, j) =>
                j == 0 ? (
                  <TableCell component="th" scope="row">
                    {col}
                  </TableCell>
                ) : (
                  <TableCell align="right">{col}</TableCell>
                )
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
