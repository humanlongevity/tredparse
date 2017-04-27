import React from 'react';
import Highlight from 'react-highlighter';
import ProbDist from './ProbDist';
import PairedEnd from './PairedEnd';
import d3 from 'd3';
import { Accordion, Alert, Table, Col, Row, Panel } from 'react-bootstrap';
import { Treds } from './TredTable';

const seqStyle = {
  fontFamily: '"Lucida Console", Monaco, monospace',
  fontSize: '10px',
};

const matchStyle = {
  backgroundColor: 'lightslategrey',
  color: 'white',
};

const TredparseResults = React.createClass({
  propTypes: {
    content: React.PropTypes.string,
    tred: React.PropTypes.string,
  },

  getStatement(calls) {
    const tred = this.props.tred;
    const tr = Treds[tred];
    const label = calls[`${tred}.label`];
    let status;

    if (label === 'ok') {
      status = 'success';
    } else if (label === 'prerisk') {
      status = 'warning';
    } else if (label === 'risk') {
      status = 'danger';
    }
    const inferredGender = calls.inferredGender;
    const depthY = calls.depthY.toFixed(3);
    let CI = calls[`${tred}.CI`];
    if (CI) CI = CI.replace('|', ' / ');

    const P_h1 = calls[`${tred}.P_h1`];
    const P_h2 = calls[`${tred}.P_h2`];
    const maxsize = d3.max(Object.keys(P_h2), d => +d);

    return (
      <div>
        <div style={{ fontSize: '24px' }}>
          <Alert bsStyle={ status }>
            { tred } alleles: { calls[`${tred}.1`] } / { calls[`${tred}.2`] } { tr.repeat }s
            <div style={{ color: 'grey' }}>
              95% Credible Interval: { CI } { tr.repeat }s
            </div>
            <div>Disease status: { label } - <span style={{ color: 'grey' }}>
              <i>Prob(disease)</i>={ Math.round(calls[`${tred}.PP`], 3) }</span>
            </div>
            { inferredGender === 'Unknown' ? null : <div>Inferred gender: { inferredGender } (chrY depth: { depthY }) </div> }
          </Alert>
        </div>
        <Panel>
          <Row>
            <Col sm={ 12 }>
              <Col sm={ 6 }>
                <div>Probability density distribution for h<sub>1</sub></div>
                <ProbDist
                  data={ P_h1 }
                  maxsize={ maxsize }
                  label={ `Number of ${tr.repeat}s in h\u2081` }
                  tred={ tred }
                />
              </Col>
              <Col sm={ 6 }>
                <div>Probability density distribution for h<sub>2</sub></div>
                <ProbDist
                  data={ P_h2 }
                  maxsize={ maxsize }
                  label={ `Number of ${tr.repeat}s in h\u2082` }
                  tred={ tred }
                />
              </Col>
            </Col>
          </Row>
        </Panel>
      </div>
    );
  },

  formatReads(reads, motif) {
    if (!reads.length) return;

    const repeat = motif.replace('N', '.');
    const regex = new RegExp(`(${repeat}){3,}`);

    return (
      <Table striped hover>
        <thead>
          <tr><td>Size</td><td>Read sequence ({ motif } tract highlighted)</td></tr>
        </thead>
        <tbody>
          { reads.map((b, index) => {
            return (
                   <tr key={ index }>
                     <td><strong>{ b.h }</strong></td>
                     <td><div style={ seqStyle }>
                       <Highlight search={ regex } matchStyle={ matchStyle }>{ b.seq }</Highlight>
                     </div></td>
                   </tr>
            );
          }) }
        </tbody>
      </Table>
    );
  },

  render() {
    const content = this.props.content;
    if (!content) return null;

    const object = JSON.parse(content);
    if (object.error) {
      return (
        <Alert bsStyle="danger">
            Execution error: { object.error }
        </Alert>
      );
    }

    const calls = object.tredCalls;
    const tred = this.props.tred;
    const tredinfo = Treds[tred];
    const details = calls[`${tred}.details`];

    const fullReads = [];
    const partialReads = [];
    const reptReads = [];
    const pairedReads = calls[`${tred}.PEDP`];
    let PEG = calls[`${tred}.PEG`];
    let PET = calls[`${tred}.PET`];
    const P_PEG = calls[`${tred}.P_PEG`];
    const P_PET = calls[`${tred}.P_PET`];

    if (PEG) PEG = PEG.replace(/[()]/g, '').replace('+/-', ' \u00B1 ');
    if (PET) PET = PET.replace(/[()]/g, '').replace('+/-', ' \u00B1 ');

    if (details) {
      details.forEach((e) => {
        if (e.tag === 'FULL') {
          fullReads.push(e);
        } else if (e.tag === 'PREF' || e.tag === 'POST') {
          partialReads.push(e);
        } else if (e.tag === 'REPT') {
          reptReads.push(e);
        }
      });
    }

    return (
      <div>
        { this.getStatement(calls) }
        <Accordion>
          <Panel header={ `Full spanning - ${fullReads.length} reads` } eventKey='1'>
            { this.formatReads(fullReads, tredinfo.repeat) }
          </Panel>
          <Panel header={ `Partial spanning - ${partialReads.length} reads` } eventKey='2'>
            { this.formatReads(partialReads, tredinfo.repeat) }
          </Panel>
          <Panel header={ `Repeat-only - ${reptReads.length} reads` } eventKey='3'>
            { this.formatReads(reptReads, tredinfo.repeat) }
          </Panel>
          <Panel header={ `Paired end - ${pairedReads} pairs` } eventKey='4'>
            <Row>
              <Col sm={ 12 }>
                <Col sm={ 6 }>
                  <div>Global paired end distance ({ PEG })</div>
                  <PairedEnd
                    data={ P_PEG }
                  />
                </Col>
                <Col sm={ 6 }>
                  <div>Local paired end distance ({ PET })</div>
                  <PairedEnd
                    data={ P_PET }
                  />
                </Col>
              </Col>
            </Row>
          </Panel>
        </Accordion>
      </div>
    );
  },
});

export default TredparseResults;
