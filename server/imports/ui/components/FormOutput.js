import React from 'react';
import { Col, Row, Panel } from 'react-bootstrap';
import AlleleFreq from './AlleleFreq';
import TredTable from './TredTable';
import IFrame from './IFrame';

const Treds = require('../../api/documents/treds.json');

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
              <AlleleFreq text={ tred.allele_frequency } />
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
