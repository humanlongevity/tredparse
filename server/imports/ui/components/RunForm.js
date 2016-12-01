import React from 'react';
import { ButtonToolbar, Button, Col, ControlLabel, FormControl, Form, FormGroup, HelpBlock } from 'react-bootstrap';

const RunForm = React.createClass({
  getInitialState() {
    return {
      value: ''
    };
  },

  getValidationState() {
    const length = this.state.value.length;
    if (length > 10) return 'success';
    else if (length > 5) return 'warning';
    else if (length > 0) return 'error';
  },

  handleChange(e) {
    this.setState({ value: e.target.value });
  },

  render() {
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
              value={this.state.value}
              placeholder="Enter sample BAM here"
              onChange={this.handleChange}
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
            <ButtonToolbar>
              <Button>HD</Button>
              <Button>SCA17</Button>
              <Button>DM1</Button>
              <Button>FRAXE</Button>
            </ButtonToolbar>
          </Col>

        </FormGroup>
      </Form>
    );
  }
});

export default RunForm;