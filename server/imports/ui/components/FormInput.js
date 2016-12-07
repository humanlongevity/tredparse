import React from 'react';
import { Meteor } from 'meteor/meteor';
import { Random } from 'meteor/random';
import { ButtonToolbar, Button, FormControl, Form, FormGroup, HelpBlock, Panel } from 'react-bootstrap';

const Treds = require('../../api/documents/treds.json');

const FormInput = React.createClass({
  propTypes: {
    clickHandler: React.PropTypes.func.isRequired,
  },

  getInitialState() {
    return {
      currentId: '',
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

  handleSubmit(e) {
    const currentId = Random.id();
    Meteor.call('shell', { _id: currentId, cmd: 'pwd' });
    this.setState({ currentId });
  },

  render() {
    const Buttons = Object.keys(Treds).map((b) => {
      return (
        <Button key={ b } onClick={ this.props.clickHandler.bind(null, b) }>
          { b }
        </Button>
      );
    });

    return (
      <Form>
        <FormGroup
          controlId="formBasicText"
          validationState={ this.getValidationState() }
        >
          <Panel header={ <strong>BAM file</strong> }>
            <FormControl
              bsSize="sm"
              type="text"
              value={ this.state.value }
              placeholder="Enter sample BAM here"
              onChange={ this.handleChange }
            />
            <FormControl.Feedback />
            <HelpBlock>
                BAM file could be either local, HTTP, or S3 (<a href='#'>Example</a>)
            </HelpBlock>
          </Panel>
        </FormGroup>

        <FormGroup>
          <Panel header={ <strong>STR locus</strong> }>
            <ButtonToolbar>
              { Buttons }
            </ButtonToolbar>
          </Panel>
        </FormGroup>

        <Button bsStyle='danger' bsSize='large' onClick={ this.handleSubmit }>
          Submit
        </Button>
        Current session Id: { this.state.currentId }
      </Form>
    );
  },
});

export default FormInput;
