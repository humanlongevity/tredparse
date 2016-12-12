import React from 'react';
import { Accordion, Alert, Table, Panel } from 'react-bootstrap';

const seqStyle = {
  fontFamily: '"Lucida Console", Monaco, monospace',
  fontSize: '12px',
  textTransform: 'uppercase',
  color: 'grey',
};

const TredparseResults = React.createClass({
  propTypes: {
    content: React.PropTypes.string,
    tred: React.PropTypes.string,
  },

  getStatement(calls) {
    const tred = this.props.tred;
    const label = calls[`${tred}.label`];
    let status;

    if (label === 'ok') {
      status = 'success';
    } else if (label === 'prerisk') {
      status = 'warning';
    } else if (label === 'risk') {
      status = 'danger';
    }

    return (
      <div style={{ fontSize: '24px' }}>
        <Alert bsStyle={ status }>
          { tred } alleles: { calls[`${tred}.1`] } / { calls[`${tred}.2`] }
          <br />
          Disease status: { label }
        </Alert>
      </div>
    );
  },

  formatReads(reads) {
    return (
      <div style={ seqStyle }>
        <Table striped hover>
          <tbody>
          { reads.map((b, index) => {
            return <tr key={ index }><td>{ b.seq }</td></tr>;
          }) }
          </tbody>
        </Table>
      </div>
    );
  },

  render() {
    const content = this.props.content;
    if (!content) return null;

    const object = JSON.parse(content);
    const calls = object.tredCalls;
    const tred = this.props.tred;
    const details = calls[`${tred}.details`];

    const fullReads = [];
    const partialReads = [];
    if (details) {
      details.forEach((e) => {
        if (e.tag === 'FULL') {
          fullReads.push(e);
        } else if (e.tag != 'HANG') {
          partialReads.push(e);
        }
      });
    }

    return (
      <div>
        { this.getStatement(calls) }
        <Accordion>
          <Panel header={ `Full spanning - ${fullReads.length} reads` } eventKey='1'>
            { this.formatReads(fullReads) }
          </Panel>
          <Panel header={`Partial spanning - ${partialReads.length} reads`} eventKey='2'>
            { this.formatReads(partialReads) }
          </Panel>
        </Accordion>
      </div>
    );
  },
});

export default TredparseResults;
