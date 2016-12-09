import React from 'react';
import { Accordion, Alert, Panel } from 'react-bootstrap';

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
            { JSON.stringify(fullReads) }
          </Panel>
          <Panel header={`Partial spanning - ${partialReads.length} reads`} eventKey='2'>
            { JSON.stringify(partialReads) }
          </Panel>
        </Accordion>
      </div>
    );
  },
});

export default TredparseResults;
