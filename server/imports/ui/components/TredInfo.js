import React from 'react';
import { Table } from 'react-bootstrap';

const Treds = require('../../api/documents/treds.json');

const TredInfo = React.createClass({
  propTypes: {
    name: React.PropTypes.string,
  },

  render() {
    const name = this.props.name;

    if (!name) {
      return null;
    }

    const tred = Treds[name];

    return (
      <Table striped condensed hover>
        <tbody>
          <tr>
            <td>Gene name</td>
            <td>{ tred.gene_name } ({ tred.gene_location }) </td>
          </tr>
          <tr>
            <td>Inheritance</td>
            <td>{ tred.inheritance }</td>
          </tr>
          <tr>
            <td>Sequence</td>
            <td>
              { tred.prefix }
              <strong>({ tred.repeat })x</strong>
              { tred.suffix }
            </td>
          </tr>
          <tr>
            <td>Symptom</td>
            <td>
              <div className="text-left">
                { tred.symptom }
              </div>
            </td>
          </tr>
        </tbody>
      </Table>
    );
  },
});

module.exports = TredInfo;