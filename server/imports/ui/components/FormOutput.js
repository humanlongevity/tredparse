import React from 'react';
import { Col, Row, Panel } from 'react-bootstrap';
import AlleleFreq from './AlleleFreq';
import TredInfo from './TredInfo';

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
        <Col sm={ 12 }>
          <Panel header={ `${name} (${tred.title})` } bsStyle="success">
            <Col sm={ 7 }>
              <TredInfo name={ name } />
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
