import React from 'react';
import { Col, Row, Panel } from 'react-bootstrap';
import AlleleFreq from './AlleleFreq';

const Treds = require('../../api/documents/treds.json');

const FormOutput = React.createClass({
  propTypes: {
    object: React.PropTypes.string,
  },

  render() {
    const object = this.props.object;

    if (!object) {
      return null;
    }

    const tred = Treds[object];
    console.log(tred);
    return (
      <Row>
        <Col sm={ 12 }>
          <Panel header={ `${object} (${tred.title})` } bsStyle="success">
            <Col sm={ 6 }>
              <div className='text-left'>
                { tred ? tred.symptom : '' }
              </div>
            </Col>
            <Col sm={ 6 }>
                <AlleleFreq text={ tred.allele_frequency } />
            </Col>
          </Panel>
        </Col>
      </Row>
    );
  },
});

export default FormOutput;
