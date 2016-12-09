import React from 'react';
import { ButtonToolbar, Button, FormControl, Form, FormGroup, HelpBlock, Panel } from 'react-bootstrap';
import Settings from './Settings';

const Treds = require('../../api/documents/treds.json');

const FormInput = React.createClass({
  propTypes: {
    clickHandler: React.PropTypes.func.isRequired,
    submitHandler: React.PropTypes.func.isRequired,
    tred: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return {
      bam: Settings.s3BAM,
    };
  },

  handleChange(e) {
    this.setState({ bam: e.target.value });
  },

  render() {
    const Buttons = Object.keys(Treds).map((b) => {
      const active = (b === this.props.tred);
      return (
        <Button key={ b }
          onClick={ this.props.clickHandler.bind(null, b) }
          active={ active }>
          { b }
        </Button>
      );
    });

    return (
      <Form>
        <FormGroup>
          <Panel header={ <strong>BAM file</strong> }>
            <FormControl
              bsSize="sm"
              type="text"
              ref='bam'
              value={ this.state.bam }
              placeholder="Enter sample BAM here"
              onChange={ this.handleChange }
            />
            <HelpBlock>
                BAM file could be either on <Button bsSize='small' bsStyle='link'
                disabled
                onClick={ () =>
                  this.setState({ bam: Settings.httpBAM })
                }>HTTP</Button> or <Button bsSize='small'
                bsStyle='link'
                onClick={ () =>
                  this.setState({ bam: Settings.s3BAM })
                }>S3</Button>
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

        <Button
          bsStyle='danger'
          bsSize='large'
          onClick={ this.props.submitHandler.bind(null, this.state.bam) }
        >
          Call { Treds[this.props.tred].title }
        </Button>
      </Form>
    );
  },
});

export default FormInput;
