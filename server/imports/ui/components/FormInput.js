import React from 'react';
import { ButtonToolbar, Button, Col, ControlLabel, FormControl, Form, FormGroup, HelpBlock } from 'react-bootstrap';

const Treds = require('../../api/documents/treds.json');

const FormInput = React.createClass({
  propTypes: {
    clickHandler: React.PropTypes.func.isRequired,
  },

  getInitialState() {
    return {
      value: '',
    };
  },

  getValidationState() {
    const length = this.state.value.length;
    if (length > 10) return 'success';
    else if (length > 5) return 'warning';
    else if (length > 0) return 'error';
    return null;
  },

  handleChange(e) {
    this.setState({ value: e.target.value });
  },

  render() {
    const Buttons = Object.keys(Treds).map((b) => {
      return <Button key={ b } onClick={ this.props.clickHandler.bind(null, b) }>{ b }</Button>;
    });

    return (
      <Form>
        <FormGroup
          controlId="formBasicText"
          validationState={this.getValidationState()}
        >
          <Col componentClass={ ControlLabel } sm={ 2 }>
            BAM
          </Col>
          <Col sm={ 10 }>
            <FormControl
              bsSize="sm"
              type="text"
              value={ this.state.value }
              placeholder="Enter sample BAM here"
              onChange={ this.handleChange }
            />
            <FormControl.Feedback />
            <HelpBlock>
                BAM file could be either HTTP-accessible or local
            </HelpBlock>
          </Col>
        </FormGroup>

        <FormGroup>
          <Col componentClass={ ControlLabel } sm={ 2 }>
            STR locus
          </Col>
          <Col sm={ 10 }>
            <div className="well">
              <ButtonToolbar>
                { Buttons }
              </ButtonToolbar>
            </div>
          </Col>
        </FormGroup>
      </Form>
    );
  },
});

export default FormInput;
