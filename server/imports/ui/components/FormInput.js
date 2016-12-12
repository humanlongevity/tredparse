import React from 'react';
import { ButtonToolbar, Button, FormControl, Form, FormGroup, HelpBlock, Panel } from 'react-bootstrap';
import Settings from './Settings';
import { Treds } from './TredTable';

const FormInput = React.createClass({
  propTypes: {
    clickHandler: React.PropTypes.func.isRequired,
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
    const buttonStyle = {
      marginBottom: '5px',
    };

    const Buttons = Object.keys(Treds).map((b) => {
      const active = (b === this.props.tred);
      return (
        <Button key={ b }
          onClick={ this.props.clickHandler.bind(null, this.state.bam, b) }
          active={ active }
          bsSize='xsmall'
          style={ buttonStyle }
        >
          <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{ b }
          </div> <div style={{ color: 'grey' }}>{ Treds[b].title }</div>
        </Button>
      );
    });

    return (
      <Form>
        <FormGroup>
          <Panel header={ <strong>BAM file</strong> }>
            <FormControl
              type="text"
              ref='bam'
              bsSize="large"
              value={ this.state.bam }
              placeholder="Enter sample BAM here"
              onChange={ this.handleChange }
            />
            <HelpBlock>
                BAM file could be on <Button bsSize='small' bsStyle='link'
                disabled
                onClick={ () =>
                  this.setState({ bam: Settings.httpBAM })
                }>HTTP</Button> or <Button bsSize='small'
                bsStyle='link'
                onClick={ () =>
                  this.setState({ bam: Settings.s3BAM })
                }>S3</Button> on human reference <strong>hg38</strong>
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
      </Form>
    );
  },
});

export default FormInput;
