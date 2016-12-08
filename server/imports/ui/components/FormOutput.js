import React from 'react';
import { Col, Row, Panel } from 'react-bootstrap';
import AlleleFreq from './AlleleFreq';
import TredTable from './TredTable';
import IFrame from './IFrame';

const Treds = require('../../api/documents/treds.json');

const FormOutput = React.createClass({
  propTypes: {
    name: React.PropTypes.string,
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
        <IFrame
          url='http://10.6.110.141/pileup/165708667/chr1/10000'
        />
        <Col sm={ 12 }>
          <Panel header={ `${name} (${tred.title})` } bsStyle="success">
            <Col sm={ 7 }>
              <TredTable name={ name } />
            </Col>
            <Col sm={ 5 }>
              <AlleleFreq text={ tred.allele_frequency } />
            </Col>
          </Panel>
        </Col>
      </Row>
    );
  },
});

export default FormOutput;
