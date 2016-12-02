import React from 'react';
import { Col, Row, Panel } from 'react-bootstrap';

const Treds = require('../../api/documents/treds.json');

const FormOutput = React.createClass({
  propTypes: {
    object: React.PropTypes.string,
  },

  render() {
    const tred = Treds[this.props.object];

    return (
      <Row>
        <Col sm={ 12 }>
          <Panel header={ this.props.object } bsStyle="success">
            { tred ? tred.title : '' }
          </Panel>
        </Col>
      </Row>
    );
  },
});

export default FormOutput;
