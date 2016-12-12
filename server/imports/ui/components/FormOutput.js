import React from 'react';
import { Col, Row, Panel } from 'react-bootstrap';
import AlleleFreq from './AlleleFreq';
import TredTable, { Treds } from './TredTable';
import IFrame from './IFrame';

const FormOutput = React.createClass({
  propTypes: {
    name: React.PropTypes.string,
    url: React.PropTypes.string,
  },

  render() {
    const name = this.props.name;

    if (!name) {
      return null;
    }

    const tred = Treds[name];
    console.log(tred);
    return (
      <Row>
        <Col sm={ 12 }>
          <Panel header={ `${name} (${tred.title})` } bsStyle="info">
            <Col sm={ 7 }>
              <TredTable name={ name } />
            </Col>
            <Col sm={ 5 }>
              <div>Allele frequency in HLI samples</div>
              <AlleleFreq
                text={ tred.allele_frequency }
                cutoffRisk={ tred.cutoff_risk }
                motif={ tred.repeat }
              />
            </Col>
          </Panel>
        </Col>
        {
          this.props.url ? <IFrame url={ this.props.url } /> : null
        }
      </Row>
    );
  },
});

export default FormOutput;
